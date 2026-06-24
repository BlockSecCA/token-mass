// extract.sc — dump a normalized graph from a Joern CPG.
//
// Emits two TSVs into $TM_OUT:
//   methods.tsv : <methodFullName>\t<file>\t<startLine>\t<endLine>
//   calls.tsv   : <callerMethodFullName>\t<calleeMethodFullName>
//
// analyze.py projects these to a file-level dependency graph. We deliberately
// keep the CPGQL minimal and proven; all graph math happens in Python so the
// extractor stays robust across Joern versions.
//
// Inputs via env (set by the `token-mass` entrypoint):
//   TM_CPG : path to the built cpg.bin
//   TM_OUT : output directory for the TSVs

import java.io.PrintWriter

val cpgPath = sys.env("TM_CPG")
val outDir  = sys.env("TM_OUT")

importCpg(cpgPath)

val pwM = new PrintWriter(s"$outDir/methods.tsv")
cpg.method.isExternal(false).foreach { m =>
  pwM.println(s"${m.fullName}\t${m.filename}\t${m.lineNumber.getOrElse(-1)}\t${m.lineNumberEnd.getOrElse(-1)}")
}
pwM.close()

val pwC = new PrintWriter(s"$outDir/calls.tsv")
cpg.call.foreach { c =>
  pwC.println(s"${c.method.fullName}\t${c.methodFullName}")
}
pwC.close()

// Import edges: <importingFile>\t<importedEntity/specifier>. For statically-typed
// languages the call graph carries cross-file edges; for dynamic ones (JS/TS/Py)
// imports are the reliable cross-file signal. analyze.py resolves specifiers to files.
val pwI = new PrintWriter(s"$outDir/imports.tsv")
cpg.imports.foreach { i =>
  val f = i.start.file.name.l.headOption.getOrElse("")
  val e = i.importedEntity.getOrElse("")
  if (f.nonEmpty && e.nonEmpty) pwI.println(s"$f\t$e")
}
pwI.close()

println(s"TM_EXTRACT_DONE -> $outDir")
