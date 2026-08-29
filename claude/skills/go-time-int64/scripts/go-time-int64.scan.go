// go-time-int64.scan.go — find time.Time / *time.Time struct fields in a Go project and
// estimate memory / GC savings from converting them to int64.
//
// Usage:
//
//	go run go-time-int64.scan.go ./...
//	go run go-time-int64.scan.go ./internal/engine ./internal/queue
//
// Pure go/ast, no type checking, no external deps. Heuristic, not exact.
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"slices"
	"sort"
	"strings"
)

type field struct {
	file, structName, fieldName string
	line                        int
	isPtr                       bool
}

type structInfo struct {
	name        string
	file        string
	line        int
	timeFields  []field
	otherPtrs   int // fields that keep the struct scannable after conversion
	inContainer []string
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: go run go-time-int64.scan.go <pkg-pattern> [...]")
		os.Exit(2)
	}
	files := collectFiles(os.Args[1:])
	if len(files) == 0 {
		fmt.Fprintln(os.Stderr, "no .go files found")
		os.Exit(1)
	}

	fset := token.NewFileSet()
	structs := map[string]*structInfo{} // key: struct name (package-local)
	var parsed []*ast.File

	for _, f := range files {
		af, err := parser.ParseFile(fset, f, nil, parser.SkipObjectResolution)
		if err != nil {
			fmt.Fprintf(os.Stderr, "skip %s: %v\n", f, err)
			continue
		}
		parsed = append(parsed, af)
		timeAlias := importAlias(af, "time")
		if timeAlias == "" {
			continue
		}
		ast.Inspect(af, func(n ast.Node) bool {
			ts, ok := n.(*ast.TypeSpec)
			if !ok {
				return true
			}
			st, ok := ts.Type.(*ast.StructType)
			if !ok {
				return true
			}
			info := &structInfo{name: ts.Name.Name, file: f, line: fset.Position(ts.Pos()).Line}
			for _, fl := range st.Fields.List {
				kind := timeKind(fl.Type, timeAlias)
				names := fl.Names
				if len(names) == 0 {
					names = []*ast.Ident{{Name: "(embedded)"}}
				}
				for _, nm := range names {
					switch kind {
					case 1, 2:
						info.timeFields = append(info.timeFields, field{
							file: f, structName: ts.Name.Name, fieldName: nm.Name,
							line: fset.Position(fl.Pos()).Line, isPtr: kind == 2,
						})
					default:
						if hasPointer(fl.Type) {
							info.otherPtrs++
						}
					}
				}
			}
			if len(info.timeFields) > 0 {
				structs[info.name] = info
			}
			return true
		})
	}

	// Second pass: find container usage of candidate structs.
	for _, af := range parsed {
		ast.Inspect(af, func(n ast.Node) bool {
			var elem ast.Expr
			var kind string
			switch t := n.(type) {
			case *ast.ArrayType:
				elem, kind = t.Elt, "slice"
			case *ast.MapType:
				if name := baseIdent(t.Key); name != "" {
					if si, ok := structs[name]; ok {
						si.inContainer = appendUnique(si.inContainer, "map-key")
					}
				}
				elem, kind = t.Value, "map-value"
			case *ast.ChanType:
				elem, kind = t.Value, "chan"
			default:
				return true
			}
			if name := baseIdent(elem); name != "" {
				if si, ok := structs[name]; ok {
					si.inContainer = appendUnique(si.inContainer, kind)
				}
			}
			return true
		})
	}

	report(structs)
}

// timeKind: 0 = not time, 1 = time.Time, 2 = *time.Time
func timeKind(e ast.Expr, alias string) int {
	if star, ok := e.(*ast.StarExpr); ok {
		if timeKind(star.X, alias) == 1 {
			return 2
		}
		return 0
	}
	sel, ok := e.(*ast.SelectorExpr)
	if !ok {
		return 0
	}
	pkg, ok := sel.X.(*ast.Ident)
	if !ok || pkg.Name != alias || sel.Sel.Name != "Time" {
		return 0
	}
	return 1
}

// hasPointer: does this field type contain a pointer word (conservative)?
func hasPointer(e ast.Expr) bool {
	switch t := e.(type) {
	case *ast.StarExpr, *ast.MapType, *ast.ChanType, *ast.FuncType, *ast.InterfaceType:
		return true
	case *ast.ArrayType:
		return t.Len == nil || hasPointer(t.Elt) // slice, or array of pointerful
	case *ast.Ident:
		return t.Name == "string" || t.Name == "error" || t.Name == "any"
	case *ast.SelectorExpr:
		return true // unknown external type: assume pointerful (conservative)
	case *ast.StructType:
		for _, f := range t.Fields.List {
			if hasPointer(f.Type) {
				return true
			}
		}
	}
	return false
}

func baseIdent(e ast.Expr) string {
	switch t := e.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.StarExpr:
		return baseIdent(t.X)
	}
	return ""
}

func importAlias(f *ast.File, path string) string {
	for _, im := range f.Imports {
		if strings.Trim(im.Path.Value, `"`) != path {
			continue
		}
		if im.Name != nil {
			if im.Name.Name == "_" || im.Name.Name == "." {
				return ""
			}
			return im.Name.Name
		}
		return path
	}
	return ""
}

func appendUnique(s []string, v string) []string {
	if slices.Contains(s, v) {
		return s
	}
	return append(s, v)
}

func collectFiles(patterns []string) []string {
	var out []string
	seen := map[string]bool{}
	for _, p := range patterns {
		recursive := strings.HasSuffix(p, "/...")
		root := strings.TrimSuffix(p, "/...")
		if root == "" {
			root = "."
		}
		filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
			if err != nil {
				return nil
			}
			if d.IsDir() {
				name := d.Name()
				if path != root && (name == "vendor" || name == "testdata" || strings.HasPrefix(name, ".") || strings.HasPrefix(name, "_")) {
					return filepath.SkipDir
				}
				if !recursive && path != root {
					return filepath.SkipDir
				}
				return nil
			}
			if strings.HasSuffix(path, ".go") && !strings.HasSuffix(path, "_test.go") && !seen[path] {
				seen[path] = true
				out = append(out, path)
			}
			return nil
		})
	}
	return out
}

func report(structs map[string]*structInfo) {
	if len(structs) == 0 {
		fmt.Println("No time.Time struct fields found.")
		return
	}
	var list []*structInfo
	for _, s := range structs {
		list = append(list, s)
	}
	// Hot candidates (in containers) first, then by number of time fields.
	sort.Slice(list, func(i, j int) bool {
		hi, hj := len(list[i].inContainer) > 0, len(list[j].inContainer) > 0
		if hi != hj {
			return hi
		}
		if len(list[i].timeFields) != len(list[j].timeFields) {
			return len(list[i].timeFields) > len(list[j].timeFields)
		}
		return list[i].name < list[j].name
	})

	fmt.Println("== time.Time → int64 candidates ==")
	fmt.Println()
	totalHot := 0
	for _, s := range list {
		saved := 0
		ptrsRemoved := 0
		for _, f := range s.timeFields {
			if f.isPtr {
				saved += 8 + 24 // pointer word + separate heap object (approx)
				ptrsRemoved += 2
			} else {
				saved += 16
				ptrsRemoved++
			}
		}
		hot := len(s.inContainer) > 0
		tag := "cold"
		if hot {
			tag = "HOT"
			totalHot++
		}
		noscan := "no (other pointer fields remain: " + fmt.Sprint(s.otherPtrs) + ")"
		if s.otherPtrs == 0 {
			noscan = "YES — struct becomes pointer-free"
		}
		fmt.Printf("[%s] %s  (%s:%d)\n", tag, s.name, s.file, s.line)
		for _, f := range s.timeFields {
			typ := "time.Time"
			if f.isPtr {
				typ = "*time.Time"
			}
			fmt.Printf("    - %-24s %-12s line %d\n", f.fieldName, typ, f.line)
		}
		if hot {
			fmt.Printf("    containers : %s\n", strings.Join(s.inContainer, ", "))
		}
		fmt.Printf("    saves/elem : ~%d bytes, %d GC pointer(s) removed\n", saved, ptrsRemoved)
		fmt.Printf("    noscan     : %s\n", noscan)
		fmt.Printf("    @1M elems  : ~%.1f MB   @100M: ~%.1f GB\n", float64(saved), float64(saved)*1e8/1e9)
		fmt.Println()
	}
	fmt.Printf("%d struct(s) with time.Time fields, %d in hot containers.\n", len(list), totalHot)
	fmt.Println("Heuristic only — confirm sizes with unsafe.Sizeof and classify per SKILL.md Phase 2.")
}
